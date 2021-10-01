# cython: language_level=2
# -*- coding: utf-8 -*-

# Original version by Yannick Versley (2013)
# Current version by Philipp Heinrich (2021)


cdef extern from "stdlib.h":
    void * malloc(int size)
    void free(void*)


cdef extern from "string.h":
    int strcmp(char*, char*)


cdef extern from "cwb/cl.h":

    int ATT_NONE
    int ATT_POS
    int ATT_STRUC
    int ATT_ALIGN
    int CDA_ESTRUC
    int CDA_EALIGN
    char * cdperror_string(int error_num)

    union c_Attribute "_Attribute"
    struct c_Corpus "TCorpus":
        pass
    struct c_CorpusProperty "TCorpusProperty":
        char * property
        char * value

    c_CorpusProperty * next
    ctypedef int CorpusCharset
    c_Attribute * cl_new_attribute(c_Corpus * corpus, char * attribute_name, int type)
    c_Corpus * cl_new_corpus(char * registry_dir, char * registry_name)
    CorpusCharset cl_corpus_charset(c_Corpus * corpus)
    char * cl_charset_name(CorpusCharset id)
    void cl_delete_corpus(c_Corpus * corpus)
    char * cl_cpos2str(c_Attribute * attribute, int position)
    int cl_cpos2id(c_Attribute * attribute, int position)
    char * cl_struc2str(c_Attribute * attribute, int position)
    bint cl_struc2cpos(c_Attribute * attribute, int position, int * start, int * end)
    int cl_str2id(c_Attribute * attribute, char * str)
    char * cl_id2str(c_Attribute * attribute, int id)
    int cl_cpos2struc(c_Attribute * attribute, int offset)
    int cl_max_struc(c_Attribute * attribute)
    int cl_max_id(c_Attribute * attribute)
    int cl_max_cpos(c_Attribute * attribute)
    bint cl_struc_values(c_Attribute * attribute)
    int * cl_id2cpos(c_Attribute * attribute, int tagid, int * result_len)
    int cl_id2freq(c_Attribute * attribute, int tagid)
    int cl_max_alg(c_Attribute * attribute)
    int cl_cpos2alg(c_Attribute * attribute, int cpos)
    int cl_alg2cpos(c_Attribute * attribute, int alg, int * source_start, int * source_end, int * target_start, int * target_end)
    int * collect_matching_ids(c_Attribute * attribute, char * pattern, int canonicalize, int * number_of_matches)
    int * cl_idlist2cpos(c_Attribute * attribute, int * ids, int number_of_ids, int sort, int * size_of_table)
    int get_struc_attribute(c_Attribute * attribute, int cpos, int * s_start, int * s_end)
    int get_num_of_struc(c_Attribute * attribute, int cpos, int * s_num)
    int get_bounds_of_nth_struc(c_Attribute * attribute, int struc_num, int * s_start, int * s_end)


cdef class Corpus:
    cdef c_Corpus * corpus
    cdef object name
    cdef object charset_decoder
    cdef object charset_encoder
    cpdef bytes to_str(self, s)
    cpdef unicode to_unicode(self, s)


cdef class IDList:
    cdef int * ids
    cdef int length
    cpdef IDList join(self, IDList other, int offset)


cdef class PosAttrib:
    cdef c_Attribute * att
    cdef Corpus parent
    cdef object attname
    cpdef cpos2id(self, int offset)


cdef class AttStruc:
    cdef c_Attribute * att
    cdef bint has_values
    cdef Corpus parent
    cdef object attname


cdef class AlignAttrib:
    cdef c_Attribute * att
    cdef bint has_values
    cdef Corpus parent
    cdef object attname
